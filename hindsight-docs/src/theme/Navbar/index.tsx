import React, {type ReactNode} from 'react';
import NavbarLayout from '@theme/Navbar/Layout';
import NavbarContent from '@theme/Navbar/Content';
import IntegrationsBanner from '@site/src/components/IntegrationsBanner';

export default function Navbar(): ReactNode {
  return (
    <>
      <NavbarLayout>
        <NavbarContent />
      </NavbarLayout>
      <IntegrationsBanner />
    </>
  );
}
