int bias = 7;
int scratch;

static void add_bias(void)
{
    scratch += bias;
}

int main(void)
{
    add_bias();
    return scratch == 7 ? 0 : 1;
}
