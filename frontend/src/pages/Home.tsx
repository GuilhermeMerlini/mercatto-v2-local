import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ProductPage } from "../api/types";
import { ProductCard } from "../components/ProductCard";
import { Spinner } from "../components/ui/Spinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import "./Home.css";

export default function Home() {
  const [categories, setCategories] = useState<string[]>([]);
  const [products, setProducts] = useState<ProductPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [categoriesRes, productsRes] = await Promise.all([
          api<string[]>("/api/catalog/categories"),
          api<ProductPage>("/api/catalog/products?page_size=12"),
        ]);
        setCategories(categoriesRes);
        setProducts(productsRes);
        setError(null);
      } catch (err) {
        setError("Erro ao carregar dados da home");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <Spinner />;
  }

  if (error) {
    return <ErrorMessage>{error}</ErrorMessage>;
  }

  return (
    <div className="home">
      <div className="home__categories">
        {categories.map((category) => (
          <Link
            key={category}
            to={`/search?category=${encodeURIComponent(category)}`}
            className="home__category-link"
          >
            {category}
          </Link>
        ))}
      </div>
      <div className="home__products">
        {products?.items.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}
