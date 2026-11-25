import { Button } from "./Button";
import "./Pagination.css";

interface PaginationProps {
  page: number;
  total: number;
  pageSize: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, total, pageSize, onChange }: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);
  
  if (totalPages <= 1) return null;
  
  const isFirstPage = page === 1;
  const isLastPage = page === totalPages;
  
  const handlePrevious = () => {
    if (!isFirstPage) onChange(page - 1);
  };
  
  const handleNext = () => {
    if (!isLastPage) onChange(page + 1);
  };
  
  return (
    <nav aria-label="Pagination" className="pagination">
      <Button
        variant="ghost"
        onClick={handlePrevious}
        disabled={isFirstPage}
      >
        Previous
      </Button>
      
      <span className="pagination__text">
        Page {page} of {totalPages}
      </span>
      
      <Button
        variant="ghost"
        onClick={handleNext}
        disabled={isLastPage}
      >
        Next
      </Button>
    </nav>
  );
}
