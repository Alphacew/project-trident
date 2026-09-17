import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Project TRIDENT — SOC Risk Intelligence Console",
  description: "Trust-Anchored Risk Intelligence, Drift & Evidence Network",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-slate-100 antialiased selection:bg-cyan-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
