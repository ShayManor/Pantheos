import { createContext, useContext } from "react";

export const Nav = createContext(null);
export const useNav = () => useContext(Nav);
