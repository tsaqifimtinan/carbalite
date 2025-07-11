import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

const cascadiaCode = JetBrains_Mono({
  variable: "--font-cascadia-code",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "carbalite",
  description: "A lightweight, open-source media processing tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${cascadiaCode.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
