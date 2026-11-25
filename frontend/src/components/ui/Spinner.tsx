import "./Spinner.css";

export function Spinner() {
  return (
    <span 
      role="status" 
      aria-label="Carregando"
      className="spinner"
    />
  );
}
