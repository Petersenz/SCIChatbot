import "./style.css";
export const metadata = {
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
