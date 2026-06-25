import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers";
import { Navbar } from "@/components/layout/Navbar";
import { Disclaimer } from "@/components/layout/Disclaimer";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Stock Intelligence Platform",
  description:
    "Análise técnica, ranking, backtesting e relatórios por IA. Uso educacional e analítico.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100">
        <Providers>
          <Navbar />
          <main className="flex-1 px-4 py-6">
            <div className="mx-auto max-w-7xl">{children}</div>
          </main>
          <Disclaimer />
        </Providers>
      </body>
    </html>
  );
}
