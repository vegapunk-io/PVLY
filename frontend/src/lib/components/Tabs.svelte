<script lang="ts">
	export interface TabItem {
		id: string;
		label: string;
		disabled?: boolean;
	}

	interface Props {
		idPrefix: string;
		items: TabItem[];
		active: string;
		label: string;
		onchange?: (id: string) => void;
	}

	let { idPrefix, items, active = $bindable(''), label, onchange }: Props = $props();
	let tablist: HTMLDivElement | undefined = $state();

	function select(id: string, focus = false): void {
		const item = items.find((candidate) => candidate.id === id);
		if (!item || item.disabled) return;
		active = id;
		onchange?.(id);
		if (focus) {
			requestAnimationFrame(() => {
				tablist?.querySelector<HTMLButtonElement>(`[data-tab-id="${CSS.escape(id)}"]`)?.focus();
			});
		}
	}

	function enabledItems(): TabItem[] {
		return items.filter((item) => !item.disabled);
	}

	function onKeyDown(event: KeyboardEvent): void {
		const enabled = enabledItems();
		if (!enabled.length) return;
		const currentIndex = Math.max(
			0,
			enabled.findIndex((item) => item.id === active)
		);

		let next: TabItem | undefined;
		if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
			next = enabled[(currentIndex + 1) % enabled.length];
		} else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
			next = enabled[(currentIndex - 1 + enabled.length) % enabled.length];
		} else if (event.key === 'Home') {
			next = enabled[0];
		} else if (event.key === 'End') {
			next = enabled.at(-1);
		}

		if (next) {
			event.preventDefault();
			select(next.id, true);
		}
	}
</script>

<div class="tabs" role="tablist" aria-label={label} bind:this={tablist}>
	{#each items as item (item.id)}
		<button
			type="button"
			role="tab"
			id={`${idPrefix}-tab-${item.id}`}
			data-tab-id={item.id}
			aria-controls={`${idPrefix}-panel-${item.id}`}
			aria-selected={active === item.id}
			tabindex={active === item.id ? 0 : -1}
			disabled={item.disabled}
			onclick={() => select(item.id)}
			onkeydown={onKeyDown}
		>
			{item.label}
		</button>
	{/each}
</div>
