'use client';
import { ArrowRight, Check, LoaderCircle, CircleAlert } from 'lucide-react';
import type { ButtonHTMLAttributes, MouseEventHandler, ElementType } from 'react';

type FlowButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ElementType;
  text?: string;
  subtitle?: string;
  href?: string;
  state?: 'idle' | 'loading' | 'error' | 'success';
};

/** Flow motion adapted from the supplied component; uses the site's yellow tokens. */
export function FlowButton({text = 'Modern Button', icon: Icon = ArrowRight, subtitle, href, state = 'idle', className = '', disabled, onClick, ...props}: FlowButtonProps) {
  const blocked = disabled || state === 'loading';
  const content = <>
    <Icon aria-hidden="true" className="flow-arrow flow-arrow-in" />
    <span className="flow-label"><span>{text}</span>{subtitle && <small>{subtitle}</small>}</span>
    <span aria-hidden="true" className="flow-circle" />
    {state === 'loading' ? <LoaderCircle aria-hidden="true" className="flow-status flow-spinner" /> : state === 'success' ? <Check aria-hidden="true" className="flow-status" /> : state === 'error' ? <CircleAlert aria-hidden="true" className="flow-status" /> : <Icon aria-hidden="true" className="flow-arrow flow-arrow-out" />}
  </>;
  const classes = `flow-button group relative flex items-center overflow-hidden text-sm font-semibold ${className}`;
  if (href) return <a href={blocked ? undefined : href} className={classes} data-state={state} aria-disabled={blocked || undefined} aria-busy={state === 'loading' || undefined} onClick={onClick as unknown as MouseEventHandler<HTMLAnchorElement>}>{content}</a>;
  return <button {...props} type={props.type || 'button'} className={classes} data-state={state} disabled={blocked} aria-busy={state === 'loading' || undefined} aria-invalid={state === 'error' || undefined} onClick={onClick}>{content}</button>;
}
