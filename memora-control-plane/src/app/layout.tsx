import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AgentProvider } from "@/lib/agent-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Memory Control Plane",
  description: "Control plane for the temporal semantic memory system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AgentProvider>
          {children}
        </AgentProvider>
      </body>
    </html>
  );
}
