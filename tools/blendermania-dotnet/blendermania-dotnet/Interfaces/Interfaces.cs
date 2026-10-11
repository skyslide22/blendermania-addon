public interface ICommand
{
    public const string COMMAND_NAME = "base-command";

    public static Task<int> Execute(string payload) => Task.FromResult(0);
}