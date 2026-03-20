import "../app/globals.css";
import DashboardLayout from "../components/DashboardLayout";

export const metadata = {
  title: "VocalSeperator - Remove Vocals from Your Songs",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className="bg-gray-50">
        <DashboardLayout>
          {children}
        </DashboardLayout>
      </body>
    </html>
  );
}