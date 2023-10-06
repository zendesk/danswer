import { Header } from "@/components/Header";
import { getAuthDisabledSS, getCurrentUserSS } from "@/lib/userSS";
import { redirect } from "next/navigation";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [authDisabled, user] = await Promise.all([
    getAuthDisabledSS(),
    getCurrentUserSS(),
  ]);

  if (!authDisabled) {
    if (!user) {
      return redirect("/auth/login");
    }
    if (user.role !== "admin") {
      return redirect("/");
    }
  }

  return (
    <div>
      <Header user={user} />
      <div className="bg-gray-900 pt-8 flex">
        <div className="px-12 min-h-screen bg-gray-900 text-gray-100 w-full">
          {children}
        </div>
      </div>
    </div>
  );
}
