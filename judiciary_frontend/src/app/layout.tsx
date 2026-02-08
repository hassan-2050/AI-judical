import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import Navbar from "@/components/layout/Navbar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

export const metadata: Metadata = {
  title: "Munsif AI | Pakistan Legal Case Database",
  description:
    "Search, browse, and analyze Pakistani legal case data from Supreme Court, High Courts, and more — powered by AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="bg-gray-50 text-gray-900 font-sans antialiased min-h-screen">
        <Toaster position="top-right" />
        <Navbar />
        <main className="min-h-[calc(100vh-64px)]">{children}</main>
      </body>
    </html>
  );
}
