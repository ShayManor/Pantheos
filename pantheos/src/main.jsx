import React from "react";
import { createRoot } from "react-dom/client";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";
import Pantheos from "./App.jsx";

createRoot(document.getElementById("root")).render(<Pantheos />);
