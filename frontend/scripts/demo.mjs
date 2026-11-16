// Runs the Prism mock (:4010) and the Vite dev server (:5173) together; stops both on exit.
import { spawn } from "node:child_process";

const children = [
  spawn("npm", ["run", "mock"], { stdio: "inherit" }),
  spawn("npm", ["run", "dev"], { stdio: "inherit" }),
];

function stopAll(code = 0) {
  for (const child of children) child.kill("SIGTERM");
  process.exit(code);
}

for (const child of children) child.on("exit", (code) => stopAll(code ?? 0));
process.on("SIGINT", () => stopAll(0));
process.on("SIGTERM", () => stopAll(0));