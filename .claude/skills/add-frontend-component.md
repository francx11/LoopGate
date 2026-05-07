# Skill: Add Frontend Component

## When to apply
Creating a new UI component (card, modal, badge, form input, etc.) in the React frontend.

## Steps

1. **Create the component file** in `frontend/src/components/MyComponent.tsx`:
   ```typescript
   import styles from "./MyComponent.module.css";
   import clsx from "clsx";

   interface Props {
     label: string;
     variant?: "default" | "accent";
     onClick?: () => void;
   }

   export function MyComponent({ label, variant = "default", onClick }: Props) {
     return (
       <div className={clsx(styles.root, variant === "accent" && styles.accent)} onClick={onClick}>
         {label}
       </div>
     );
   }
   ```

2. **Create co-located CSS Module** `frontend/src/components/MyComponent.module.css`:
   ```css
   .root {
     /* Use CSS vars — never hardcode colors */
     background: var(--surface);
     color: var(--text);
     border-radius: 8px;
     padding: 0.75rem 1rem;
   }

   .accent {
     background: var(--accent);      /* #7c6af7 */
     color: #fff;
   }
   ```

3. **Available CSS variables** (from `frontend/src/index.css`):
   | Var | Value | Use |
   |---|---|---|
   | `--bg` | `#0a0a0f` | Page background |
   | `--surface` | dark card color | Card/panel background |
   | `--accent` | `#7c6af7` | Interactive purple |
   | `--green` | `#4ade80` | Success/done |
   | `--red` | `#f87171` | Error/reject |
   | `--text` | `#e8e8f0` | Primary text |
   | `--text-muted` | dimmer text | Secondary labels |

4. **Import and use** in a page (`Dashboard.tsx`, `SetupScreen.tsx`) or parent component:
   ```typescript
   import { MyComponent } from "../components/MyComponent";
   ```

5. **If reading from store**:
   ```typescript
   import { useStore } from "../store";
   const tasks = useStore((s) => s.tasks);
   ```

6. **If calling API**:
   ```typescript
   import { myAction } from "../services/api";
   ```

## What not to do
- Don't use inline `style={{}}` for colors — always CSS vars via class
- Don't use Tailwind utility classes directly in JSX (project uses CSS Modules + Tailwind config, not inline utilities)
- Don't manage async state with `useState` + `useEffect` for API calls that are already in the WS stream — read from the Zustand store instead
- Don't write UI text in English — labels and messages must be in Spanish
- Don't add a light theme variant
