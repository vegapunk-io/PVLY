import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

// Query-preserving legacy redirect; search params are unavailable while prerendering.
export const prerender = false;

export const load: PageLoad = ({ url }) => {
	throw redirect(307, `/rules${url.search}`);
};
