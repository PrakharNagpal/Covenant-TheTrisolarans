import { Tag } from "@/components/ui/Tag";
import { tokens, type SourceKey } from "@/lib/tokens";

type SourceBadgeProps = {
  source: SourceKey;
};

export function SourceBadge({ source }: SourceBadgeProps) {
  const config = tokens.source[source];

  return (
    <Tag color={config.color} bg={config.bg}>
      <span className="mr-1" aria-hidden="true">
        {config.emoji}
      </span>
      {config.label}
    </Tag>
  );
}
