"""Generate 10 scanned Urdu legal PDFs and paired ground-truth pages for OCR CER benchmarking."""

from pathlib import Path
import random
from PIL import Image, ImageFilter
import pymupdf


SCANNED_DIR = Path("data_sources/scanned_urdu")
BENCHMARK_DIR = Path("data_sources/ocr_benchmark")

URDU_DOCS = [
    (
        "01_kiraya_nama_lahore",
        "معاہدہ کرایہ داری (کرایہ نامہ)",
        "یہ معاہدہ کرایہ داری آج مورخہ ۱۵ جنوری ۲۰۲۵ء بمقام لاہور، فریق اول محمد طارق (مالک مکان) اور فریق دوم علی رضا (کرایہ دار) کے درمیان طے پایا۔ مکان نمبر ۴۲، بلاک بی، گلبرگ لاہور کا ماہانہ کرایہ پچاس ہزار روپے مقرر کیا گیا ہے۔ کرایہ دار ہر ماہ کی پانچ تاریخ تک کرایہ ادا کرنے کا پابند ہوگا۔ معاہدے کی مدت گیارہ ماہ ہوگی اور بجلی و گیس کے بل کرایہ دار ادا کرے گا۔",
    ),
    (
        "02_fir_report_karachi",
        "ابتدائی اطلاعی رپورٹ (ایف آئی آر)",
        "تھانہ صدر کراچی، ضلع جنوبی۔ اطلاع کنندہ کا نام: سلیم احمد ولد رشید احمد، ساکن لیاری کراچی۔ تاریخ وقوعہ: ۱۰ فروری ۲۰۲۵ء بوقت شام چھ بجے۔ ملزمان نامعلوم موٹر سائیکل پر آئے اور اسلحہ کے زور پر موبائل فون اور نقدی پینتیس ہزار روپے چھین کر فرار ہوگئے۔ مقدمہ زیر دفعہ ۳۹۲ تعزیرات پاکستان درج کر کے تفتیش شروع کر دی گئی ہے۔",
    ),
    (
        "03_qanooni_notice_islamabad",
        "قانونی نوٹس برائے ادائیگی واجبات",
        "جناب من، میں اپنے موکل خان اینڈ ایسوسی ایٹس اسلام آباد کی ہدایت پر آپ کو مطلع کرتا ہوں کہ معاہدہ مورخہ یکم ستمبر ۲۰۲۴ء کے تحت تین لاکھ روپے کے واجبات تاحال ادا نہیں کیے گئے۔ آپ کو چودہ یوم کی مہلت دی جاتی ہے کہ مکمل رقم مع سود ادا کریں، بصورت دیگر فوجداری و دیوانی عدالت میں دعویٰ دائر کیا جائے گا۔",
    ),
    (
        "04_darkhwast_zamanat_rawalpindi",
        "درخواست ضمانت بعد از گرفتاری",
        "بعدالت جناب سیشن جج صاحب راولپنڈی۔ عنوان: محمد عمران بنام سرکار۔ مقدمہ نمبر ۲۱۴/۲۰۲۴، جرم زیر دفعہ ۴۸۹ ایف تعزیرات پاکستان، تھانہ سول لائنز راولپنڈی۔ سائل بے گناہ ہے اور اسے بدنیتی کی بنیاد پر مقدمے میں ملوث کیا گیا ہے۔ چالان عدالت میں پیش ہو چکا ہے اور مزید تفتیش درکار نہیں، لہٰذا ضمانت منظور فرمائی جائے۔",
    ),
    (
        "05_bayan_e_halfi_multan",
        "بیان حلفی برائے ملکیت جائیداد",
        "منکہ زاہدہ پروین زوجہ اکرم خان، ساکن ماڈل ٹاؤن ملتان، بقائمی ہوش و حواس بیان حلفی دیتی ہوں کہ پلاٹ نمبر ۱۸، رقبہ دس مرلہ واقع بوسن روڈ ملتان میری قانونی ملکیت ہے اور اس پر کسی بینک یا فرد کا کوئی قرضہ یا کفالت قائم نہیں ہے۔ میرا یہ بیان حلفی بالکل درست ہے اور کوئی امر مخفی نہیں رکھا گیا۔",
    ),
    (
        "06_iqrarnama_farokht_faisalabad",
        "اقرار نامہ فروخت اراضی",
        "یہ اقرار نامہ فروخت آج مورخہ ۲۰ مارچ ۲۰۲۵ء کو فریق اول حاجی اسلم اور فریق دوم ندیم اختر کے درمیان طے پایا۔ فریق اول نے اپنی زرعی اراضی رقبہ چار ایکڑ واقع تحصیل جڑانوالہ ضلع فیصل آباد مبلغ اسی لاکھ روپے میں فروخت کرنے کا معاہدہ کیا ہے۔ بیعانہ مبلغ بیس لاکھ روپے وصول پایا اور بقیہ رقم رجسٹری کے وقت ادا ہوگی۔",
    ),
    (
        "07_mulazmat_muahida_peshawar",
        "ملازمت کا تقرری نامہ و معاہدہ",
        "خیبر ٹیکنالوجیز پرائیویٹ لمیٹڈ پشاور کی جانب سے جناب کامران یوسف کو بطور سافٹ ویئر انجینئر تعینات کیا جاتا ہے۔ ماہانہ تنخواہ ایک لاکھ بیس ہزار روپے مقرر کی گئی ہے۔ ملازمت کے پہلے تین ماہ آزمائشی ہوں گے۔ ملازم کمپنی کے خفیہ ڈیٹا اور تجارتی رازوں کی حفاظت کا پابند ہوگا۔",
    ),
    (
        "08_mukhtar_nama_aam_quetta",
        "مختار نامہ عام",
        "منکہ عبداللہ جان ولد گل محمد، ساکن جناح روڈ کوئٹہ، بذریعہ ہذا اپنے بھائی ساجد خان کو اپنا مختار عام مقرر کرتا ہوں۔ مختار عام کو اختیار حاصل ہے کہ وہ میری غیر موجودگی میں ضلع کوئٹہ میں واقع میری تمام منقولہ و غیر منقولہ جائیداد کی دیکھ بھال کرے، سرکاری دفاتر اور عدالتوں میں میری نمائندگی و پیروی کرے۔",
    ),
    (
        "09_dawa_naan_nafaqa_sialkot",
        "دعویٰ دلاپانے خرچہ نان و نفقہ",
        "بعدالت جناب فیملی جج صاحب سیالکوٹ۔ مدعیہ: آمنہ بی بی بنت محمد اشرف، بمقابلہ مدعا علیہ: بلال حسین ولد غلام رسول۔ مدعیہ کا نکاح مدعا علیہ کے ساتھ ۲۰۱۹ء میں ہوا تھا اور دو کمسن بچے ہیں۔ مدعا علیہ گزشتہ دو سال سے خرچہ نان و نفقہ ادا نہیں کر رہا، لہٰذا تیس ہزار روپے ماہانہ خرچہ کی ڈگری صادر فرمائی جائے۔",
    ),
    (
        "10_hukamnama_adalat_lahore",
        "حکم نامہ عدالت عالیہ لاہور",
        "عدالت عالیہ لاہور، رٹ پٹیشن نمبر ۴۵۱۲/۲۰۲۵۔ فریقین کے وکلاء کے دلائل سنے گئے۔ ریکارڈ کا بغور جائزہ لینے کے بعد عدالت اس نتیجے پر پہنچی ہے کہ متعلقہ اتھارٹی کا حکم مورخہ ۱۲ دسمبر ۲۰۲۴ء قانون کے منافی اور اختیار سے تجاوز ہے۔ لہٰذا پٹیشن منظور کرتے ہوئے متنازعہ نوٹیفکیشن کالعدم قرار دیا جاتا ہے۔",
    ),
]


def render_urdu_page_to_scan(doc_id: str, title: str, body: str) -> None:
    """Render Urdu text via PyMuPDF Story, convert to scanned image-only PDF + PNG + ground truth."""
    html = (
        '<div dir="rtl" style="font-family: Tahoma, Arial, sans-serif; '
        'line-height: 1.9; color: #111111;">'
        f'<h2 style="font-size: 18pt; margin-bottom: 14pt; text-align: center;">{title}</h2>'
        f'<p style="font-size: 14pt; text-align: justify;">{body}</p>'
        "</div>"
    )
    temp_pdf = BENCHMARK_DIR / f"{doc_id}_digital_tmp.pdf"
    story = pymupdf.Story(html=html)
    writer = pymupdf.DocumentWriter(str(temp_pdf))
    rect = pymupdf.paper_rect("a4")
    dev = writer.begin_page(rect)
    story.place(rect + (54, 60, -54, -60))
    story.draw(dev, None)
    writer.end_page()
    writer.close()
    del writer
    del story

    # Rasterize at 180 DPI and add slight realistic scanner tilt + blur
    pdf_doc = pymupdf.open(temp_pdf)
    pix = pdf_doc[0].get_pixmap(dpi=180, colorspace=pymupdf.csGRAY)
    pdf_doc.close()
    del pdf_doc
    temp_pdf.unlink(missing_ok=True)

    img = Image.frombytes("L", [pix.width, pix.height], pix.samples)
    rng = random.Random(doc_id)
    angle = rng.uniform(-0.6, 0.6)
    img = img.rotate(angle, resample=Image.Resampling.BICUBIC, fillcolor=250)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.35))

    png_path = BENCHMARK_DIR / f"{doc_id}.png"
    img.save(png_path)

    # Save exact Unicode ground-truth text
    gt_path = BENCHMARK_DIR / f"{doc_id}.txt"
    gt_path.write_text(f"{title}\n{body}\n", encoding="utf-8")

    # Wrap rasterized image into an image-only PDF in scanned_urdu/ (no text layer!)
    scanned_pdf_path = SCANNED_DIR / f"{doc_id}_scanned.pdf"
    out_pdf = pymupdf.open()
    page = out_pdf.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, filename=str(png_path))
    out_pdf.save(scanned_pdf_path)
    out_pdf.close()


def main() -> None:
    SCANNED_DIR.mkdir(parents=True, exist_ok=True)
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    for doc_id, title, body in URDU_DOCS:
        render_urdu_page_to_scan(doc_id, title, body)
        print(f"  [OK] {doc_id}: scanned PDF + benchmark PNG + ground truth .txt")

    print(
        f"\nGenerated {len(URDU_DOCS)} scanned Urdu docs. "
        f"Total PDFs in {SCANNED_DIR}: {len(list(SCANNED_DIR.glob('*.pdf')))}"
    )


if __name__ == "__main__":
    main()
