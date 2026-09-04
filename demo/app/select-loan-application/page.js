import { redirect } from "next/navigation";

export default function LegacySelectionRoute() {
  redirect("/application-flow/approve");
}
