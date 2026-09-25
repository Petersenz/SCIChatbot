export const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

// Stored references stay deployment-neutral. Prefix local browser URLs only.
export function publicUrl(value: string): string {
  if (!basePath || !value.startsWith("/") || value.startsWith("//") ||
      value === basePath || value.startsWith(basePath + "/")) return value;
  return basePath + value;
}

export function appPath(value: string): string {
  if (basePath && (value === basePath || value.startsWith(basePath + "/"))) {
    return value.slice(basePath.length) || "/";
  }
  return value;
}
