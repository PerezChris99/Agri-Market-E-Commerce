# Contributing to Agri-Market

Thank you for your interest in Agri-Market. This project is a production-oriented agricultural marketplace, and changes can affect customers, farmers, sellers, payments, inventory, delivery operations, privacy, and security. Contributions are therefore reviewed deliberately.

**Contact the project owner first. Do not begin implementation, integrate a vendor, or submit a pull request until you have received explicit written approval and an agreed scope.** A proposal or conversation is not approval.

## 1. Start with a proposal

Email **kweeziperez712@gmail.com** with the subject:

`Agri-Market Contribution Proposal — [Short description]`

Include the following:

1. **Who you are:** your name, GitHub username or company, and the role you would play.
2. **Your experience:** relevant skills, experience level, and links to relevant work, repositories, or examples. Be candid about what you have and have not built before.
3. **What you want to add or change:** describe the specific feature, fix, integration, or documentation improvement.
4. **Why it matters:** explain the user or business problem it solves and who benefits.
5. **Why the existing system is insufficient:** point to the relevant current behavior, code, documentation, or limitation. First inspect the repository and README; do not assume a capability is missing because it is not obvious from the UI or because you sell a tool that could provide it.
6. **Your proposed approach:** outline the design, affected parts of the application, alternatives considered, and likely maintenance burden.
7. **How you would verify it:** propose tests, acceptance criteria, and how you would demonstrate that the change works without breaking existing behavior.
8. **Operational impact:** disclose new dependencies, external services, credentials, personal/customer data involved, recurring costs, hosting needs, and deployment or migration requirements.

Do not include passwords, API keys, private customer information, production data, or other secrets in your proposal.

## 2. Confirm the gap before writing code

A proposal must explain the difference between what the platform already does and what the proposed change would enable. The owner may ask questions or request a small investigation before deciding.

Examples of questions to answer:

- Does a similar capability already exist in the codebase?
- Is the limitation real, reproducible, and in scope?
- Can the requirement be met by improving existing code rather than adding a duplicate system?
- Does the change introduce a vendor lock-in, ongoing fee, new data-sharing arrangement, or avoidable security risk?
- What happens if the provider is unavailable, becomes too expensive, or the integration needs to be removed?

A sales pitch, unsolicited vendor email, or claim that a product could be useful is not by itself evidence that the project needs it.

## 3. Wait for explicit written approval

Do not start coding, open a pull request, connect a provider, request production credentials, run migrations, deploy services, or make changes to project infrastructure until the owner has explicitly approved the proposal in writing.

Approval should establish the agreed scope, expected outcome, boundaries, acceptance criteria, and who is responsible for any external costs or accounts. Approval for one task does not authorize unrelated changes or future work. If the scope changes, pause and obtain approval for the revised scope.

The owner may decline, defer, narrow, or redirect a proposal. Please do not treat silence as consent.

## 4. Requirements for approved work

Once approved, contributions are expected to:

- Solve the agreed problem with the smallest maintainable change that meets the requirements.
- Follow the existing architecture and established project conventions unless an architectural change was approved.
- Preserve authentication, authorization, privacy, payment verification, inventory consistency, order integrity, auditability, and tenant/ownership boundaries.
- Include meaningful automated tests for new behavior, regressions, failure paths, and security-sensitive logic.
- Update relevant documentation, configuration examples, and operational guidance.
- Avoid unnecessary dependencies, duplicated functionality, hidden network calls, telemetry, tracking, and unrelated refactors.
- Never commit secrets, live credentials, customer data, production database dumps, private keys, or generated runtime artifacts.
- Explain new environment variables and use safe placeholders in examples.
- Disclose migrations, backfills, provider requirements, recurring costs, rollback steps, and any production-only verification that cannot be completed locally.

Never test against live customer data or production payment/delivery systems without specific written authorization and an agreed safe test plan.

## 5. Pull request expectations

Only submit a pull request after the work has been approved and implemented within the agreed scope. The pull request should explain:

- The problem and evidence that the current system does not already solve it.
- The approved scope and user/business benefit.
- What changed and which application areas are affected.
- Tests and checks run, with results; clearly identify checks that could not be run.
- Security, privacy, reliability, performance, accessibility, and compatibility implications where relevant.
- New dependencies, third-party services, costs, data flows, environment variables, migrations, and deployment steps.
- Failure handling, rollback/removal strategy, and any remaining limitations.

Keep changes focused and reviewable. Do not bundle unrelated features or change licensing, repository settings, branch protections, secrets, deployment configuration, or workflows without separate explicit approval. Opening a pull request does not guarantee acceptance or merging.

## 6. Third-party products and commercial proposals

If you represent a company or are proposing a commercial service, disclose that relationship at the outset. Include pricing and likely recurring costs, contract or account requirements, data collected and where it is processed, retention/deletion behavior, security documentation, service limits, support arrangements, alternatives, and an exit plan.

Do not send unsolicited production credentials, ask for access to customer data, or connect your service to this project without written approval. The project is not obligated to adopt, advertise, or endorse a vendor product.

## 7. Copyright, permissions, and third-party material

The project and its original source code, documentation, architecture, designs, and other original materials are claimed as proprietary to the copyright holder. The repository's `LICENSE` file contains the project's proprietary rights notice. Public visibility of the repository does not, by itself, grant permission to use, copy, modify, redistribute, or create derivative works from the project.

Obtain explicit written permission and agree on applicable terms before beginning any contribution or other use. A contribution proposal, pull request, or acceptance of work does not automatically transfer ownership or grant a license; rights and terms must be expressly agreed in writing. The owner may require a separate written contributor agreement for a particular contribution.

Contributors must have the right to submit their work and must not improperly copy third-party or employer-owned material. Identify reused code, assets, datasets, and other materials along with their applicable rights and terms. Third-party components remain subject to their respective owners' terms. This guide and the proprietary notice do not purport to remove rights that applicable law does not allow the copyright holder to exclude.

## 8. Communication and conduct

Be respectful, factual, and open about uncertainty. Report security concerns privately to the owner rather than publishing exploit details or sensitive information in an issue or pull request. Do not disclose vulnerabilities publicly before coordinating a responsible response.

## Contributor checklist

Before you begin, confirm that you have:

- [ ] Contacted the owner with your experience, proposed change, and rationale.
- [ ] Investigated the current codebase and explained why existing functionality is insufficient.
- [ ] Disclosed dependencies, providers, costs, data handling, and operational requirements.
- [ ] Received explicit written approval and an agreed scope.
- [ ] Agreed on acceptance criteria and a safe test plan.

Before submitting approved work, confirm that you have:

- [ ] Added or updated appropriate tests and documentation.
- [ ] Kept secrets and real customer/production data out of Git.
- [ ] Documented risks, migrations, deployment needs, and rollback steps.
- [ ] Described what was tested and what remains unverified in the pull request.

---

**The process starts with a proposal, not a pull request. Contact the project owner first and wait for written approval before beginning work.**
