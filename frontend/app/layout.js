import "./globals.css";
import Nav from "@/components/Nav";

export const metadata = {
  title: "LMS-ERP Integration Platform",
  description: "College ERP integrated with Moodle LMS",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
