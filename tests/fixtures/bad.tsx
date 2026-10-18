import { ChevronRight, ArrowLeft, Send } from "lucide-react";

export default function Header() {
  return (
    <header className="flex pl-6 md:mr-auto rounded-l-lg border-r-2 -ml-1 left-0">
      <button className="hover:ml-2"><ArrowLeft className="h-4 w-4" /></button>
      <ChevronRight className="size-4" />
      <Send className="size-4" />
      <p style={{ marginLeft: 8, textAlign: "left" }}>مرحبا</p>
      <input type="email" className="border" />
      <input autoComplete="tel" />
    </header>
  );
}
