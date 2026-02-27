import React from 'react';
import Link from '@docusaurus/Link';
import styles from './CookbookGrid.module.css';

export interface CookbookCard {
  title: string;
  href: string;
  description?: string;
  tags?: {
    sdk?: string;
    topic?: string;
  };
}

interface CookbookGridProps {
  items: CookbookCard[];
}

function Card({title, href, description, tags}: CookbookCard) {
  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cardBody}>
        <h3 className={styles.cardTitle}>{title}</h3>
        {description && <p className={styles.cardDescription}>{description}</p>}
        {(tags?.topic || tags?.sdk) && (
          <div className={styles.cardFooter}>
            {tags.topic && <span className={styles.cardTopic}>{tags.topic}</span>}
            {tags.sdk && <span className={styles.cardSdk}>{tags.sdk}</span>}
          </div>
        )}
      </div>
    </Link>
  );
}

export default function CookbookGrid({items}: CookbookGridProps) {
  return (
    <div className={styles.grid}>
      {items.map((item) => (
        <Card key={item.href} {...item} />
      ))}
    </div>
  );
}
