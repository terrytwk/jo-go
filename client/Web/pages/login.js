import Head from "next/head";

const Login = () => {
  return (
    <div>
      <Head>
        <title>Jo Go | Log In</title>
        <meta
          name="description"
          content="Official website for Jo-Go - Final project for MIT 6.08 Intro to EECS via Interconnected Embedded Systems class, which automates the distribution of Arduino parts to the students, which used to done manually by TAs."
        />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <input placeholder="MIT Email" />
        <input placeholder="Student ID" />
        <input type="submit" />
      </div>
    </div>
  );
};

export default Login;
