import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DubDeck AI",
  description: "Production AI video dubbing SaaS"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

