import "./style.css";
import { publicUrl } from "../components/paths";
export const metadata = {
  icons: { icon: [{ url: publicUrl("/brand/sci-chatbot.png"), type: "image/png" }] },
  title: "ไซน์แชทบอท | คณะวิทยาศาสตร์และเทคโนโลยี",
  description:
    "ระบบแนะแนวการศึกษา คณะวิทยาศาสตร์และเทคโนโลยี มหาวิทยาลัยราชภัฏเพชรบูรณ์",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body>
        <a className="skip" href="#main">
          ข้ามไปยังเนื้อหา
        </a>
        {children}
      </body>
    </html>
  );
}
