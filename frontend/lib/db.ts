import postgres from "postgres";

// Return date/timestamp columns as ISO strings instead of Date objects.
// Date objects can't be passed from Server Components to Client Components.
const dateAsString = {
  serialize: (x: string) => x,
  parse: (x: string) => x,
};

const sql = postgres(process.env.DATABASE_URL!, {
  ssl: process.env.NODE_ENV === "production" ? "require" : false,
  max: 10,
  types: {
    date:        { to: 1082, from: [1082],        ...dateAsString },
    time:        { to: 1083, from: [1083],        ...dateAsString },
    timestamp:   { to: 1114, from: [1114, 1184],  ...dateAsString },
  },
});

export default sql;
