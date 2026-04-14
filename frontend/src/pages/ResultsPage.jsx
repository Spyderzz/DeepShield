import { useParams } from 'react-router-dom';

export default function ResultsPage() {
  const { id } = useParams();
  return (
    <section>
      <h2>Results</h2>
      <p>Analysis ID: {id}</p>
    </section>
  );
}
