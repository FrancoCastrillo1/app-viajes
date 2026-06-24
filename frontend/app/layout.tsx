import type { Metadata } from "next";
import { Toaster } from "sonner";
import { Playfair_Display, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import LayoutShell from "@/components/LayoutShell";
import { getSession } from "@/lib/auth";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Ruta Compartida",
  description: "Viajes compartidos en Argentina. Encontrá personas que hacen tu misma ruta y compartí los gastos.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  return (
    <html lang="es" className={`${playfair.variable} ${jakarta.variable}`}>
      <body>
        <Toaster position="bottom-right" richColors />
        <LayoutShell userId={session.userId}>
          {children}
        </LayoutShell>
      </body>
    </html>
  );
}
