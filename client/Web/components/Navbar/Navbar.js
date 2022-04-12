import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { MenuItems } from "./MenuItems";
import Button from "../Button";
import styles from "./Navbar.module.css";

import { AiOutlineMenu, AiOutlineClose } from "react-icons/ai";

const Navbar = () => {
  const [clicked, setClicked] = useState(false);

  return (
    <nav className={styles["NavbarItems"]}>
      {/* <Link href="/" className="navbar-logo">
        <a>
          <Image src="" alt="Logo" height={100} with={100} />
        </a>
      </Link> */}
      <Link href="/" className={styles["navbar-logo"]}>
        <a className={styles["navbar-logo-text"]}>Jo Go</a>
      </Link>

      <div className={styles["menu-icon"]} onClick={() => setClicked(!clicked)}>
        {clicked ? <AiOutlineClose /> : <AiOutlineMenu />}
      </div>
      <ul
        className={
          clicked
            ? `${styles["nav-menu"]} ${styles["active"]}`
            : styles["nav-menu"]
        }
      >
        {MenuItems.map((item, index) => {
          return (
            <li key={index}>
              <a href={item.url} className={styles[item.cName]}>
                {item.title}
              </a>
            </li>
          );
        })}
      </ul>
      <Link href="/login" passHref>
        <Button id="button">Log In</Button>
      </Link>
    </nav>
  );
};

export default Navbar;
