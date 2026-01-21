import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
  const sucursalId = url.searchParams.get('sucursal_id');
  
  return {
    sucursalId
  };
};
