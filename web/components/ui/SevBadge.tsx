import { Tag } from "@/components/ui/Tag";
import { tokens, type SeverityKey } from "@/lib/tokens";

type SevBadgeProps = {
  severity: SeverityKey;
};

export function SevBadge({ severity }: SevBadgeProps) {
  const config = tokens.severity[severity];

  return <Tag color={config.color} bg={config.bg}>{config.label}</Tag>;
}
