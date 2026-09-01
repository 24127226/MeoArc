import { Fragment, type ReactNode } from 'react'

/**
 * VanBanDep — dựng câu trả lời của trợ lý thành VĂN BẢN CÓ CẤU TRÚC.
 *
 * ── KHÔNG TỐN THÊM MỘT TOKEN NÀO ──
 * Đây là câu hỏi đáng hỏi trước khi làm, và câu trả lời là KHÔNG. Mô hình vốn đã
 * viết ra Markdown (`**đậm**`, `- gạch đầu dòng`, `### tiêu đề`) — đó là thói quen
 * mặc định của mọi LLM. Trước đây ta VỨT BỎ cấu trúc đó: `whitespace-pre-line` chỉ
 * giữ được dấu xuống dòng, còn các ký hiệu thì hiện nguyên xi ra màn hình dưới dạng
 * dấu sao và dấu thăng.
 *
 * Nên việc ở đây thuần là ĐỌC LẠI thứ đã có sẵn trong chuỗi trả về. Không prompt
 * thêm, không gọi model thêm, không đổi gì ở backend. Cùng một câu trả lời, cùng một
 * chi phí — chỉ khác ở chỗ nó được hiển thị đúng hình dạng mà mô hình đã định.
 *
 * ── VÌ SAO DỰNG PHẦN TỬ REACT, KHÔNG PHẢI dangerouslySetInnerHTML ──
 * Nội dung này do MÔ HÌNH sinh ra, và mô hình đọc nội dung thư của người dùng. Một lá
 * thư chứa `<img onerror=...>` mà lọt qua được là lỗ hổng chèn mã ngay trong hộp thư.
 * Dựng phần tử thì chuỗi không bao giờ được diễn giải thành HTML — đóng hẳn lớp lỗ
 * hổng đó, thay vì phải tin vào một bộ lọc.
 *
 * Cố ý CHỈ hiểu vài thứ hay dùng nhất. Nhúng cả một thư viện Markdown vào đây là thêm
 * ~40KB và thêm một mặt tấn công, để đổi lấy những cú pháp (bảng, chú thích, HTML
 * nhúng) mà trợ lý gần như không bao giờ dùng khi trả lời hội thoại.
 */

/** In đậm, in nghiêng, mã, và liên kết — xử lý TRONG một dòng. */
function trongDong(raw: string, khoa: string): ReactNode[] {
  const ra: ReactNode[] = []
  // Một biểu thức duy nhất cho cả bốn dạng: thứ tự nhánh quan trọng — `**` phải đứng
  // trước `*`, nếu không "**đậm**" bị đọc thành nghiêng-rỗng-nghiêng.
  const mau = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\[[^\]]+\]\((?:https?:\/\/)[^)\s]+\))/g
  let cuoi = 0
  let m: RegExpExecArray | null
  let i = 0

  while ((m = mau.exec(raw)) !== null) {
    if (m.index > cuoi) ra.push(raw.slice(cuoi, m.index))
    const t = m[0]
    const k = `${khoa}-${i++}`

    if (t.startsWith('**')) {
      ra.push(<strong key={k} className="font-semibold text-foreground">{t.slice(2, -2)}</strong>)
    } else if (t.startsWith('`')) {
      ra.push(
        <code key={k} className="rounded bg-foreground/8 px-1 py-px font-mono text-[0.88em]">
          {t.slice(1, -1)}
        </code>,
      )
    } else if (t.startsWith('[')) {
      const cat = t.indexOf('](')
      const nhan = t.slice(1, cat)
      const url = t.slice(cat + 2, -1)
      ra.push(
        // `noreferrer noopener`: liên kết do mô hình sinh ra, và trang đích có thể là
        // bất kỳ đâu — không để nó với tới cửa sổ này qua `window.opener`.
        <a key={k} href={url} target="_blank" rel="noreferrer noopener"
           className="text-[var(--spark)] underline underline-offset-2 hover:opacity-80">
          {nhan}
        </a>,
      )
    } else {
      ra.push(<em key={k} className="italic">{t.slice(1, -1)}</em>)
    }
    cuoi = m.index + t.length
  }
  if (cuoi < raw.length) ra.push(raw.slice(cuoi))
  return ra
}

type Khoi =
  | { loai: 'doan'; dong: string[] }
  | { loai: 'gach'; muc: string[] }
  | { loai: 'so'; muc: string[] }
  | { loai: 'de'; chu: string; bac: number }

/** Gom các dòng thành KHỐI. Phải gom trước khi vẽ: một gạch đầu dòng nằm giữa hai
 *  đoạn văn chỉ đúng khi cả cụm liền nhau được bọc trong CÙNG một `<ul>`. */
function gomKhoi(text: string): Khoi[] {
  const ra: Khoi[] = []
  for (const dong of text.split('\n')) {
    const s = dong.trim()
    const cuoi = ra[ra.length - 1]

    if (!s) { if (cuoi?.loai === 'doan') ra.push({ loai: 'doan', dong: [] }); continue }

    const de = /^(#{1,4})\s+(.*)$/.exec(s)
    if (de) { ra.push({ loai: 'de', bac: de[1].length, chu: de[2] }); continue }

    const gach = /^[-*•]\s+(.*)$/.exec(s)
    if (gach) {
      if (cuoi?.loai === 'gach') cuoi.muc.push(gach[1])
      else ra.push({ loai: 'gach', muc: [gach[1]] })
      continue
    }

    const so = /^\d+[.)]\s+(.*)$/.exec(s)
    if (so) {
      if (cuoi?.loai === 'so') cuoi.muc.push(so[1])
      else ra.push({ loai: 'so', muc: [so[1]] })
      continue
    }

    if (cuoi?.loai === 'doan') cuoi.dong.push(s)
    else ra.push({ loai: 'doan', dong: [s] })
  }
  return ra.filter((k) => k.loai !== 'doan' || k.dong.length > 0)
}

export function VanBanDep({ text }: { text: string }) {
  const khoi = gomKhoi(text)
  return (
    <div className="flex flex-col gap-2">
      {khoi.map((k, i) => {
        if (k.loai === 'de') {
          return (
            <p key={i} className={k.bac <= 2
              ? 'mt-0.5 text-[14px] font-semibold text-foreground'
              : 'mt-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground'}>
              {trongDong(k.chu, `d${i}`)}
            </p>
          )
        }
        if (k.loai === 'gach') {
          return (
            <ul key={i} className="flex flex-col gap-1">
              {k.muc.map((m, j) => (
                <li key={j} className="flex gap-2">
                  {/* Chấm tròn tự vẽ chứ không dùng `list-disc`: cần canh ĐÚNG dòng
                      đầu của mục, còn marker mặc định thì trôi khi chữ xuống dòng. */}
                  <span className="mt-[7px] size-1 shrink-0 rounded-full bg-[var(--spark)]" />
                  <span className="min-w-0">{trongDong(m, `g${i}-${j}`)}</span>
                </li>
              ))}
            </ul>
          )
        }
        if (k.loai === 'so') {
          return (
            <ol key={i} className="flex flex-col gap-1">
              {k.muc.map((m, j) => (
                <li key={j} className="flex gap-2">
                  <span className="mt-px shrink-0 font-mono text-[11px] font-semibold tabular-nums text-[var(--spark)]">
                    {j + 1}.
                  </span>
                  <span className="min-w-0">{trongDong(m, `s${i}-${j}`)}</span>
                </li>
              ))}
            </ol>
          )
        }
        return (
          <p key={i} className="break-words">
            {k.dong.map((d, j) => (
              <Fragment key={j}>
                {j > 0 && <br />}
                {trongDong(d, `p${i}-${j}`)}
              </Fragment>
            ))}
          </p>
        )
      })}
    </div>
  )
}
