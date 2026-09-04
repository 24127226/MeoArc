import { useMemo } from 'react'
import { AlertTriangle, ArrowUpRight, Clock, Inbox } from 'lucide-react'
import type { Email } from '@/data/emails'
import { trichCamKet, apLucTheoNgay, TRAN_MOI_NGAY, type CamKet } from '@/lib/cam-ket'
import { cn } from '@/lib/utils'
import { t } from '@/lib/ngon-ngu'

/**
 * CommitmentsView — "Việc của tôi": dòng thời gian cam kết trích từ hộp thư.
 *
 * ── VÌ SAO KHÔNG PHẢI MỘT LƯỚI THÁNG ──
 * Lưới tháng dựng ra để XẾP CHỖ: ô nào trống thì nhét việc vào. Nhưng thứ người
 * dùng cần biết không phải "thứ Năm còn trống không", mà "thứ Năm tôi có chết
 * không". Đó là câu hỏi về ÁP LỰC, và một lưới ô vuông không trả lời được — nó
 * cho mọi ngày cùng một kích thước bất kể ngày đó nặng hay nhẹ.
 *
 * Nên màn này mở đầu bằng ba vạch áp lực, rồi mới tới danh sách. Vạch trả lời
 * câu hỏi thật trước khi liệt kê chi tiết.
 *
 * ── VÌ SAO CÓ MỤC KHÔNG CÓ GIỜ ──
 * "Trả lời thầy Sơn" không có thời điểm nào cả, nên một cuốn lịch không chứa nổi
 * nó. Mà đó lại đúng là loại việc hay bị quên nhất — bạn gửi thư hỏi một thứ,
 * năm ngày rồi chưa ai đáp, và không công cụ nào theo dõi.
 */
export function CommitmentsView({
  emails,
  onOpenEmail,
}: {
  emails: Email[]
  onOpenEmail: (id: string) => void
}) {
  const camKet = useMemo(() => trichCamKet(emails), [emails])
  const apLuc = useMemo(() => apLucTheoNgay(camKet, 5), [camKet])
  const conLai = camKet.filter((c) => c.trangThai !== 'xong')

  return (
    <div className="kinh-mo den-vien flex h-full w-full flex-col overflow-y-auto scrollbar-thin p-5">
      <header className="mb-5 shrink-0">
        <div className="flex items-baseline gap-2.5">
          <h2 className="text-[19px] font-semibold leading-none tracking-tight text-foreground">
            Việc của tôi
          </h2>
          <span className="font-mono text-[12px] tabular-nums text-[var(--spark)]">
            {String(conLai.length).padStart(2, '0')}
          </span>
        </div>
        <p className="mt-2 flex items-center gap-1.5 text-[9.5px] uppercase tracking-[0.2em] text-muted-foreground/60">
          <span className="pulse-dot" aria-hidden />
          Trích từ hộp thư · chưa ghi vào lịch
        </p>
      </header>

      {/* ── VẠCH ÁP LỰC — đặt TRÊN danh sách, không phải dưới.
          Nó trả lời câu hỏi thật ("ngày nào tôi vỡ trận") trước khi bắt người
          dùng đọc từng dòng. Ngày chạm trần đổi sang màu cấp 2, nên vấn đề đọc
          được mà chưa cần đọc chữ nào. */}
      <div className="mb-6 flex shrink-0 flex-col gap-2">
        {apLuc.map((a) => {
          const tyLe = Math.min(1, a.phut / TRAN_MOI_NGAY)
          const quaTai = a.phut > TRAN_MOI_NGAY
          return (
            <div key={a.ngay.toISOString()} className="flex items-center gap-3">
              <span className="w-9 shrink-0 font-mono text-[11px] text-muted-foreground">
                {tenThu(a.ngay)}
              </span>
              <span className="relative h-[5px] flex-1 overflow-hidden bg-foreground/10">
                <i
                  className="absolute inset-y-0 left-0 block transition-[width] duration-500"
                  style={{
                    width: `${Math.max(tyLe * 100, a.phut > 0 ? 4 : 0)}%`,
                    background: quaTai
                      ? 'linear-gradient(90deg, var(--rr-can), var(--rr-khong))'
                      : 'var(--rr-hoan)',
                  }}
                />
              </span>
              <span className="w-12 shrink-0 text-right font-mono text-[11px] tabular-nums text-muted-foreground">
                {a.phut ? `${(a.phut / 60).toFixed(1).replace('.0', '')} g` : '—'}
              </span>
            </div>
          )
        })}
      </div>

      {conLai.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
          <span className="o-icon size-12 [--tint:var(--rr-hoan)]">
            <Inbox className="size-5" />
          </span>
          <p className="max-w-[260px] text-[13px] leading-relaxed text-muted-foreground">
            Chưa thấy cam kết nào trong hộp thư. MeoArc chỉ nhận việc khi thư có đủ
            cả mốc thời gian lẫn dấu hiệu nghĩa vụ — thà bỏ sót còn hơn nhồi rác vào
            danh sách việc.
          </p>
        </div>
      ) : (
        <div className="flex flex-col">
          {conLai.map((c) => (
            <DongCamKet key={c.id} ck={c} onOpen={() => onOpenEmail(c.emailId)} />
          ))}
        </div>
      )}
    </div>
  )
}

function DongCamKet({ ck, onOpen }: { ck: CamKet; onOpen: () => void }) {
  const nghiNgo = ck.doTinCay < 0.6
  return (
    <button
      onClick={onOpen}
      className={cn(
        'goc-cat group grid w-full grid-cols-[52px_1fr_auto] items-start gap-3 border-t',
        'border-foreground/[0.07] px-1 py-3.5 text-left transition-colors hover:bg-foreground/[0.03]',
      )}
    >
      <span className="pt-0.5 font-mono text-[11px] leading-tight tabular-nums text-muted-foreground">
        {ck.han ? (
          <>
            {tenThu(ck.han)}
            <br />
            {gioPhut(ck.han)}
          </>
        ) : (
          '—'
        )}
      </span>

      <span className="flex min-w-0 flex-col gap-1">
        <span className="truncate text-[14px] font-medium text-foreground">{ck.noiDung}</span>
        <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11.5px] text-muted-foreground">
          <span className="truncate">{ck.nguoiCho} đang chờ</span>
          {ck.uocLuongPhut > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3" />
                {ck.uocLuongPhut >= 60
                  ? t('ck.hours', { n: ck.uocLuongPhut / 60 })
                  : t('ck.minutes', { n: ck.uocLuongPhut })}
              </span>
            </>
          )}
          {ck.hanSuyRa && (
            <>
              <span className="text-muted-foreground/40">·</span>
              {/* Hạn SUY RA phải nói rõ là suy ra. Người dùng cần biết con số này
                  do MeoArc tính chứ không có sẵn trong thư — để họ kiểm được. */}
              <span className="text-[var(--rr-can)]">{t('st.inferredDue')}</span>
            </>
          )}
        </span>
      </span>

      <span className="flex shrink-0 items-center gap-2">
        {/* Độ tin cậy thấp → HỎI, đừng tự khẳng định. Một hạn nộp bị đọc sai ngày
            còn tệ hơn hẳn không có hạn nào: người dùng tin vào nó rồi trễ thật. */}
        {nghiNgo && (
          <span className="rui-ro-2 goc-cat-nho goc-cat inline-flex items-center gap-1 px-2 py-1
                           font-mono text-[9px] font-semibold uppercase tracking-[0.1em] text-[var(--rr-can)]">
            <AlertTriangle className="size-2.5" />
            Chưa chắc
          </span>
        )}
        <span
          className={cn(
            'goc-cat-nho goc-cat px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-[0.1em]',
            ck.mucRuiRo === 2 ? 'rui-ro-2 text-[var(--rr-can)]' : 'rui-ro-1 text-[var(--rr-hoan)]',
          )}
        >
          {t(ck.trangThai === 'dang_doi' ? 'flt.waiting' : ck.mucRuiRo === 2 ? 'ck.urgent' : 'ck.todo')}
        </span>
        <ArrowUpRight className="mt-0.5 size-3.5 shrink-0 text-muted-foreground/40 transition-colors group-hover:text-foreground" />
      </span>
    </button>
  )
}

const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
function tenThu(d: Date): string {
  const homNay = new Date()
  homNay.setHours(0, 0, 0, 0)
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  const cach = Math.round((x.getTime() - homNay.getTime()) / 86400000)
  if (cach === 0) return 'Nay'
  if (cach === 1) return 'Mai'
  return THU[d.getDay()]
}
function gioPhut(d: Date): string {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
