import React from 'react';
import Link from '@docusaurus/Link';
import styles from './RecipeCarousel.module.css';

export interface RecipeCard {
  title: string;
  href: string;
}

interface RecipeCarouselProps {
  title: string;
  items: RecipeCard[];
}

export default function RecipeCarousel({ title, items }: RecipeCarouselProps): React.ReactElement {
  return (
    <div className={styles.carouselSection}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <div className={styles.carousel}>
        <div className={styles.carouselTrack}>
          {items.map((item, index) => (
            <Link key={index} to={item.href} className={styles.card}>
              <span className={styles.cardTitle}>{item.title}</span>
              <span className={styles.cardLink}>→</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
