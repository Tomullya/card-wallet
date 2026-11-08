import { ApiError } from "../api";

/** Shows what went wrong, using the API's own message and field details. */
export default function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : "Something went wrong";
  const details = error instanceof ApiError ? error.details : undefined;
  return (
    <div className="banner" role="alert" data-testid="error-banner">
      {message}
      {details && details.length > 0 && (
        <ul>
          {details.map((d) => (
            <li key={d.field + d.problem}>
              {d.field}: {d.problem}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
