import type { Metadata } from "next";
import "./global.css";

export const metadata: Metadata = {
  title: "BlogForge — AI Blog Generation Engine",
  description: "GEO-optimized, AI-powered blog generation from keyword intent to ranked content.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}