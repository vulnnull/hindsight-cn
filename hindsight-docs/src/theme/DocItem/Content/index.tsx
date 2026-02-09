import React from 'react';
import DocItemContent from '@theme-original/DocItem/Content';
import type DocItemContentType from '@theme/DocItem/Content';
import type { WrapperProps } from '@docusaurus/types';
import CopyPageButton from '@site/src/components/CopyPageButton';
import styles from './styles.module.css';

type Props = WrapperProps<typeof DocItemContentType>;

export default function DocItemContentWrapper(props: Props): JSX.Element {
  return (
    <>
      <div className={styles.docItemHeader}>
        <div className={styles.docItemActions}>
          <CopyPageButton />
        </div>
      </div>
      <DocItemContent {...props} />
    </>
  );
}