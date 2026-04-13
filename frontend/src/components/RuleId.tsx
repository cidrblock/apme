import { Tooltip } from '@patternfly/react-core';
import { getRuleDescription } from '../data/ruleDescriptions';
import { bareRuleId } from './severity';

function SingleRuleId({ ruleId, className }: { ruleId: string; className?: string }) {
  const desc = getRuleDescription(ruleId);
  const bare = bareRuleId(ruleId);
  const span = <span className={className ?? 'apme-rule-id'}>{bare}</span>;
  return desc ? <Tooltip content={desc}>{span}</Tooltip> : span;
}

export function RuleId({ ruleId, className }: { ruleId: string; className?: string }) {
  const ids = ruleId.split(',').map((s) => s.trim()).filter(Boolean);
  if (ids.length <= 1) {
    return <SingleRuleId ruleId={ruleId} className={className} />;
  }
  return (
    <>
      {ids.map((id, i) => (
        <span key={id}>
          {i > 0 && ','}
          <SingleRuleId ruleId={id} className={className} />
        </span>
      ))}
    </>
  );
}
