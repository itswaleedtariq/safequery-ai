import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="not-found-page">
      <div>
        <p className="eyebrow">PAGE NOT FOUND</p>
        <h1>That route does not exist.</h1>
        <p>Return to the project overview or open the query workspace.</p>
        <Link className="button button-primary" to="/">
          Return home
        </Link>
      </div>
    </main>
  );
}