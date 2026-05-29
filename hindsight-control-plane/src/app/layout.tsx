import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hindsight 控制台",
  description: "时序语义记忆系统控制台",
  icons: {
    icon: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="bg-background text-foreground">
        <ThemeProvider>
          <FeaturesProvider>
            <BankProvider>{children}</BankProvider>
          </FeaturesProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  );
}
