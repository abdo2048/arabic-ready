import { ChevronRight, ArrowLeft, Send, Play, Check } from "lucide-react";

export default function Header() {
  return (
    <html lang="ar" dir="rtl">
      <header className="flex ps-6 md:me-auto rounded-s-lg border-e-2 -ms-1 start-0 rtl:space-x-reverse">
        <button className="hover:ms-2"><ArrowLeft className="h-4 w-4 rtl:-scale-x-100" /></button>
        <ChevronRight className="size-4 rtl:rotate-180" />
        <Send className="size-4 rtl:-scale-x-100" />
        <Play className="size-4" />
        <Check className="size-4" />
        <p style={{ marginInlineStart: 8, textAlign: "start" }}>مرحبا</p>
        <input type="email" dir="ltr" className="border text-end" />
        <div className="ltr:ml-2 rtl:mr-2" />
        <div className="translate-x-2 inset-x-0 mx-auto px-4" />
      </header>
    </html>
  );
}
