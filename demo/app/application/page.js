import { redirect } from "next/navigation";

export default function LegacyApplicationRoute() {
  redirect("/application-flow/approve");
}
