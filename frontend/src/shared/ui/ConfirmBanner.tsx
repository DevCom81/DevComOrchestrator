type ConfirmBannerProps = {
  message: string;
};

export function ConfirmBanner({ message }: ConfirmBannerProps) {
  return (
    <div className="confirm-banner" role="status" aria-live="polite">
      {message}
    </div>
  );
}
