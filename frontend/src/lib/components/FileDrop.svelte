<script lang="ts">
	import { MAX_UPLOAD_BYTES, SCAN_ACCEPT } from '../api';
	import { formatBytes } from '../format';
	import Icon from './Icon.svelte';

	interface Props {
		id: string;
		name?: string;
		label: string;
		description?: string;
		files?: File[];
		multiple?: boolean;
		accept?: string;
		maxFiles?: number;
		maxBytes?: number;
		disabled?: boolean;
		required?: boolean;
		onchange?: (files: File[]) => void;
	}

	let {
		id,
		name,
		label,
		description = 'Image, video, audio, document or text file · up to 200 MB',
		files = $bindable([]),
		multiple = false,
		accept = SCAN_ACCEPT,
		maxFiles = 1,
		maxBytes = MAX_UPLOAD_BYTES,
		disabled = false,
		required = false,
		onchange
	}: Props = $props();

	let input: HTMLInputElement | undefined = $state();
	let dragDepth = $state(0);
	let error = $state('');

	const hintId = $derived(`${id}-hint`);
	const errorId = $derived(`${id}-error`);
	const isDragging = $derived(dragDepth > 0);
	const effectiveMaxFiles = $derived(multiple ? maxFiles : 1);

	function publish(next: File[]): void {
		files = next;
		onchange?.(next);
	}

	function acceptFiles(incoming: File[]): void {
		error = '';
		if (!incoming.length) return;

		const candidates = multiple ? [...files, ...incoming] : incoming.slice(0, 1);
		if (candidates.length > effectiveMaxFiles) {
			error = `Choose no more than ${effectiveMaxFiles} file${effectiveMaxFiles === 1 ? '' : 's'} at a time.`;
			return;
		}

		const invalid = candidates.find((file) => !file.size || file.size > maxBytes);
		if (invalid) {
			error = !invalid.size
				? `“${invalid.name}” is empty.`
				: `“${invalid.name}” is ${formatBytes(invalid.size)}, above the ${formatBytes(maxBytes)} limit.`;
			return;
		}

		const unique = candidates.filter(
			(file, index, all) =>
				all.findIndex(
					(candidate) =>
						candidate.name === file.name &&
						candidate.size === file.size &&
						candidate.lastModified === file.lastModified
				) === index
		);
		publish(unique);
	}

	function onInputChange(event: Event): void {
		const target = event.currentTarget as HTMLInputElement;
		acceptFiles(Array.from(target.files ?? []));
		target.value = '';
	}

	function hasFiles(event: DragEvent): boolean {
		return Array.from(event.dataTransfer?.types ?? []).includes('Files');
	}

	function onDragEnter(event: DragEvent): void {
		if (disabled || !hasFiles(event)) return;
		event.preventDefault();
		dragDepth += 1;
	}

	function onDragOver(event: DragEvent): void {
		if (disabled || !hasFiles(event)) return;
		event.preventDefault();
		if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy';
	}

	function onDragLeave(event: DragEvent): void {
		if (disabled || !hasFiles(event)) return;
		event.preventDefault();
		dragDepth = Math.max(0, dragDepth - 1);
	}

	function onDrop(event: DragEvent): void {
		if (disabled) return;
		event.preventDefault();
		dragDepth = 0;
		acceptFiles(Array.from(event.dataTransfer?.files ?? []));
	}

	function onPaste(event: ClipboardEvent): void {
		if (disabled) return;
		const pasted = Array.from(event.clipboardData?.files ?? []);
		if (!pasted.length) return;
		event.preventDefault();
		acceptFiles(pasted);
	}

	function removeFile(index: number): void {
		publish(files.filter((_, fileIndex) => fileIndex !== index));
		error = '';
		input?.focus();
	}
</script>

<div class="file-drop">
	<label
		class="file-drop__surface"
		class:is-dragging={isDragging}
		class:is-disabled={disabled}
		for={id}
		ondragenter={onDragEnter}
		ondragover={onDragOver}
		ondragleave={onDragLeave}
		ondrop={onDrop}
		onpaste={onPaste}
	>
		<input
			bind:this={input}
			class="visually-hidden"
			{id}
			{name}
			type="file"
			{accept}
			{multiple}
			{disabled}
			required={required && !files.length}
			aria-required={required ? 'true' : undefined}
			aria-describedby={`${hintId}${error ? ` ${errorId}` : ''}`}
			aria-invalid={error ? 'true' : undefined}
			onchange={onInputChange}
		/>
		<span class="file-drop__icon" aria-hidden="true"><Icon name="upload" size={26} /></span>
		<span class="file-drop__title">{isDragging ? 'Release to add the file' : label}</span>
		<span class="file-drop__description" id={hintId}>{description}</span>
		<span class="file-drop__button">{multiple ? 'Choose files' : 'Choose file'}</span>
		<span class="file-drop__paste">or paste a file here after selecting this area</span>
	</label>

	{#if error}
		<p class="field-error" id={errorId} role="alert">{error}</p>
	{/if}

	{#if files.length}
		<ul class="file-list" aria-label="Selected files">
			{#each files as file, index (`${file.name}-${file.size}-${file.lastModified}`)}
				<li>
					<span class="file-list__icon" aria-hidden="true"><Icon name="file" size={20} /></span>
					<span class="file-list__copy">
						<strong>{file.name}</strong>
						<span>{formatBytes(file.size)}{file.type ? ` · ${file.type}` : ''}</span>
					</span>
					<button
						class="file-list__remove"
						type="button"
						aria-label={`Remove ${file.name}`}
						onclick={() => removeFile(index)}
						{disabled}
					>
						<Icon name="x" size={18} />
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.file-drop__surface {
		align-items: center;
		background: var(--canvas-soft);
		border: 1.5px dashed #8b8376;
		border-radius: var(--radius);
		color: var(--body);
		cursor: pointer;
		display: flex;
		flex-direction: column;
		font-weight: var(--fw-regular);
		margin: 0;
		padding: clamp(1.5rem, 4vw, 2.3rem) 1.2rem;
		text-align: center;
		transition:
			background-color 160ms ease,
			border-color 160ms ease;
	}

	.file-drop__surface:hover,
	.file-drop__surface:focus-within {
		border-color: var(--primary);
	}

	.file-drop__surface:focus-within {
		box-shadow: var(--focus-ring);
	}

	.file-drop__surface.is-dragging {
		background: var(--primary-soft);
		border-color: var(--primary);
		color: var(--ink);
	}

	.file-drop__surface.is-disabled {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.file-drop__icon {
		align-items: center;
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: 50%;
		color: var(--primary-hover);
		display: inline-flex;
		height: 3.3rem;
		justify-content: center;
		margin-bottom: 0.9rem;
		width: 3.3rem;
	}

	.file-drop__title {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: clamp(1.25rem, 3vw, 1.5rem);
		font-weight: var(--fw-display-strong);
		letter-spacing: -0.03em;
		line-height: 1.2;
	}

	.file-drop__description {
		font-size: 0.93rem;
		margin-top: 0.45rem;
		max-width: 560px;
	}

	.file-drop__button {
		background: var(--ink);
		border-radius: 10px;
		color: var(--on-primary);
		font-weight: var(--fw-semibold);
		margin-top: 1.1rem;
		min-height: 44px;
		padding: 0.62rem 1.1rem;
	}

	.file-drop__paste {
		color: var(--body-mid);
		font-size: 0.82rem;
		margin-top: 0.65rem;
	}

	.file-list {
		display: grid;
		gap: 0.6rem;
		list-style: none;
		margin: 0.85rem 0 0;
		padding: 0;
	}

	.file-list li {
		align-items: center;
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: 10px;
		display: flex;
		gap: 0.75rem;
		padding: 0.7rem;
	}

	.file-list__icon {
		color: var(--primary-hover);
		line-height: 0;
	}

	.file-list__copy {
		display: grid;
		flex: 1;
		line-height: 1.35;
		min-width: 0;
	}

	.file-list__copy strong {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.file-list__copy span {
		color: var(--body-mid);
		font-size: 0.85rem;
	}

	.file-list__remove {
		align-items: center;
		background: var(--canvas-soft);
		border: 1px solid var(--line);
		border-radius: 8px;
		color: var(--ink);
		cursor: pointer;
		display: inline-flex;
		height: 44px;
		justify-content: center;
		width: 44px;
	}

	.file-list__remove:hover {
		border-color: var(--bad);
		color: var(--bad);
	}
</style>
