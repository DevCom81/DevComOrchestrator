type ErrorStateProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "Une erreur est survenue",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="button button--secondary" onClick={onRetry}>
          Réessayer
        </button>
      ) : null}
    </div>
  );
}
