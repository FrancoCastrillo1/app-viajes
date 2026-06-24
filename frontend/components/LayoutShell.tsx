"use client";

import { useState } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

interface LayoutShellProps {
  userId?: number;
  children: React.ReactNode;
}

export default function LayoutShell({ userId, children }: LayoutShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        userId={userId}
      />
      <Navbar
        userId={userId}
        onOpenSidebar={() => setSidebarOpen(true)}
      />
      <main>{children}</main>
      <Footer />
    </>
  );
}
